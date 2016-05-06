GLClient.controller('MainCtrl', ['$q', '$scope', '$rootScope', '$http', '$route', '$routeParams', '$location',  '$filter', '$translate', '$uibModal', '$timeout', 'Authentication', 'Node', 'Contexts', 'Receivers', 'WhistleblowerTip', 'fieldUtilities', 'GLCache', 'GLTranslate',
  function($q, $scope, $rootScope, $http, $route, $routeParams, $location, $filter, $translate, $uibModal, $timeout, Authentication, Node, Contexts, Receivers, WhistleblowerTip, fieldUtilities, GLCache, GLTranslate) {
    $rootScope.started = false;
    $rootScope.showLoadingPanel = false;
    $rootScope.successes = [];
    $rootScope.errors = [];

    $rootScope.embedded = $location.search().embedded === 'true' ? true : false;

    $rootScope.get_auth_headers = Authentication.get_auth_headers;

    $scope.dumb_function = function() {
      return true;
    };

    $scope.iframeCheck = function() {
      try {
        return window.self !== window.top;
      } catch (e) {
        return true;
      }
    };

    $scope.browserNotCompatible = function() {
      document.getElementById("BrowserSupported").style.display = "none";
      document.getElementById("BrowserNotSupported").style.display = "block";
    };

    $scope.update = function (model, cb, errcb) {
      var success = {};
      model.$update(function() {
        $rootScope.successes.push(success);
      }).then(
        function() { if (cb !== undefined){ cb(); } },
        function() { if (errcb !== undefined){ errcb(); } }
      );
    };

    $scope.go = function (hash) {
      $location.path(hash);
    };

    $scope.randomFluff = function () {
      return Math.random() * 1000000 + 1000000;
    };

    $scope.imgDataUri = function(data) {
      if (data === '') {
        data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgDTD2qgAAAAASUVORK5CYII=';
      }

      return 'data:image/png;base64,' + data;
    };

    $scope.isWizard = function () {
      var path = $location.path();
      return path === '/wizard';
    };

    $scope.isHomepage = function () {
      var path = $location.path();
      return path === '/';
    };

    $scope.isLoginPage = function () {
      var path = $location.path();
      return (path === '/login' ||
              path === '/admin' ||
              path === '/receipt');
    };

    $scope.isAWhistleblowerPage = function() {
      var path = $location.path();
      return (path === '/' ||
              path === '/start' ||
              path === '/submission' ||
              path === '/receipt' ||
              path === '/status');
    };

    $scope.showLoginForm = function () {
      return (!$scope.isHomepage() &&
              !$scope.isLoginPage());
    };

    $scope.showPrivacyBadge = function() {
      return (!$rootScope.embedded &&
              !$rootScope.node.disable_privacy_badge &&
              $scope.isAWhistleblowerPage());
    };

    $scope.hasSubtitle = function () {
      return $scope.header_subtitle !== '';
    };

    $scope.set_title = function () {
      if ($rootScope.node) {
        var path = $location.path();
        var statuspage = '/status';
        if (path === '/') {
          $scope.ht = $rootScope.node.header_title_homepage;
        } else if (path === '/submission') {
          $scope.ht = $rootScope.node.header_title_submissionpage;
        } else if (path === '/receipt') {
          if (Authentication.keycode) {
            $scope.ht = $rootScope.node.header_title_receiptpage;
          } else {
            $scope.ht = $filter('translate')("Login");
          }
        } else if (path.substr(0, statuspage.length) === statuspage) {
          $scope.ht = $rootScope.node.header_title_tippage;
        } else {
          $scope.ht = $filter('translate')($scope.header_title);
        }
      }
    };

    $scope.route_check = function () {
      if ($rootScope.node) {
        if ($rootScope.node.wizard_done === false) {
          $location.path('/wizard');
        }

        if (($location.path() === '/') && ($rootScope.node.landing_page === 'submissionpage')) {
          $location.path('/submission');
        }

        if ($location.path() === '/submission' &&
            $scope.anonymous === false &&
            $rootScope.node.tor2web_whistleblower === false) {
          $location.path("/");
        }
      }
    };

    $scope.show_file_preview = function(content_type) {
      var content_types = [
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/bmp'
      ];

      return content_types.indexOf(content_type) > -1;
    };

    $scope.getXOrderProperty = function() {
      return 'x';
    };

    $scope.getYOrderProperty = function(elem) {
      var key = 'presentation_order';
      if (elem[key] === undefined) {
        key = 'y';
      }
      return key;
    };

    $scope.moveUp = function(elem) {
      elem[$scope.getYOrderProperty(elem)] -= 1;
    };

    $scope.moveDown = function(elem) {
      elem[$scope.getYOrderProperty(elem)] += 1;
    };

    $scope.moveLeft = function(elem) {
      elem[$scope.getXOrderProperty(elem)] -= 1;
    };

    $scope.moveRight = function(elem) {
      elem[$scope.getXOrderProperty(elem)] += 1;
    };

    $scope.deleteFromList = function(list, elem) {
      var idx = list.indexOf(elem);
      if (idx !== -1) {
        list.splice(idx, 1);
      }
    };

    $scope.assignUniqueOrderIndex = function(elements) {
      if (elements.length <= 0) {
        return;
      }

      var key = $scope.getYOrderProperty(elements[0]);
      if (elements.length) {
        var i = 0;
        elements = $filter('orderBy')(elements, key);
        angular.forEach(elements, function (element) {
          element[key] = i;
          i += 1;
        });
      }
    };

    $scope.closeAlert = function(list, index) {
      list.splice(index, 1);
    };

    $rootScope.getUploadUrl_lang = function(lang) {
      return 'admin/l10n/' + lang + '.json';
    };

    $scope.init = function () {
      var deferred = $q.defer();

      Node.get(function(node, getResponseHeaders) {
        $rootScope.node = node;
        // Tor detection and enforcing of usage of HS if users are using Tor
        if (window.location.hostname.match(/^[a-z0-9]{16}\.onion$/)) {
          // A better check on this situation would be
          // to fetch https://check.torproject.org/api/ip
          $rootScope.anonymous = true;
        } else {
          if (window.location.protocol === 'https:') {
             var headers = getResponseHeaders();
             if (headers['x-check-tor'] !== undefined && headers['x-check-tor'] === 'true') {
               $rootScope.anonymous = true;
               if ($rootScope.node.hidden_service && !$scope.iframeCheck()) {
                 // the check on the iframe is in order to avoid redirects
                 // when the application is included inside iframes in order to not
                 // mix HTTPS resources with HTTP resources.
                 window.location.href = $rootScope.node.hidden_service + '/#' + $location.url();
               }
             } else {
               $rootScope.anonymous = false;
             }
          } else {
            $rootScope.anonymous = false;
          }
        }

        GLTranslate.AddNodeFacts(node.default_language, node.languages_enabled);

        $scope.route_check();

        $scope.languages_supported = {};
        $scope.languages_enabled = {};
        $scope.languages_enabled_selector = [];
        angular.forEach(node.languages_supported, function (lang) {
          var code = lang.code;
          var name = lang.native;
          $scope.languages_supported[code] = name;
          if (node.languages_enabled.indexOf(code) !== -1) {
            $scope.languages_enabled[code] = name;
            $scope.languages_enabled_selector.push({"name": name, "code": code});
          }
        });

        $scope.languages_enabled_selector = $filter('orderBy')($scope.languages_enabled_selector, 'code');

        $scope.languages_enabled_length = Object.keys(node.languages_enabled).length;

        $scope.show_language_selector = ($scope.languages_enabled_length > 1);

        $scope.set_title();

        if ($scope.node.enable_experimental_features) {
          $scope.isStepTriggered = fieldUtilities.isStepTriggered;
          $scope.isFieldTriggered = fieldUtilities.isFieldTriggered;
        } else {
          $scope.isStepTriggered = $scope.dumb_function;
          $scope.isFieldTriggered = $scope.dumb_function;
        }

        var q1 = Contexts.query(function (contexts) {
          $rootScope.contexts = contexts;
        });

        var q2 = Receivers.query(function (receivers) {
          $rootScope.receivers = receivers;
        });

        $q.all([q1.$promise, q2.$promise]).then(function() {
          $scope.started = true;
          deferred.resolve();
        });

      });

      return deferred.promise;
    };

    $scope.view_tip = function(keycode) {
      keycode = keycode.replace(/\D/g,'');
      new WhistleblowerTip(keycode, function() {
        $location.path('/status');
      });
    };

    $scope.orderByY = function(row) {
      return row[0].y;
    };

    $scope.remove = function(array, index){
      array.splice(index, 1);
    };

    $scope.exportJSON = function(data, filename) {
      var json = angular.toJson(data, 2);
      var blob = new Blob([json], {type: "application/json"});
      filename = filename === undefined ? 'data.json' : filename;
      saveAs(blob, filename);
    };

    $scope.reload = function(new_path) {
      $rootScope.started = false;
      $rootScope.successes = [];
      $rootScope.errors = [];
      GLCache.removeAll();
      $scope.init().then(function() {
        $route.reload();

        if (new_path) {
          $location.path(new_path).replace();
        }
      });
    };

    $scope.uploadedFiles = function(uploads) {
      var sum = 0;

      angular.forEach(uploads, function(flow) {
        if (flow !== undefined) {
          sum += flow.files.length;
        }
      });

      return sum;
    };

    $scope.getUploadStatus = function(uploads) {
      var error = false;

      for (var key in uploads) {
        if (uploads.hasOwnProperty(key)) {
          if (uploads[key].files.length > 0 && uploads[key].progress() != 1) {
            return 'uploading';
          }

          for (var i=0; i<uploads[key].files.length; i++) {
            if (uploads[key].files[i].error) {
              error = true;
              break;
            }
          }
        }
      }

      if (error) {
        return 'error';
      } else {
        return 'finished';
      }
    };

    $scope.isUploading = function(uploads) {
      return $scope.getUploadStatus(uploads) === 'uploading';
    };

    $scope.remainingUploadTime = function(uploads) {
      var sum = 0;

      angular.forEach(uploads, function(flow) {
        var x = flow.timeRemaining();
        if (x === 'Infinity') {
          return 'Infinity';
        }
        sum += x;
      });

      return sum;
    };

    $scope.uploadProgress = function(uploads) {
      var sum = 0;
      var n = 0;

      angular.forEach(uploads, function(flow) {
        sum += flow.progress();
        n += 1;
      });

      if (n === 0 || sum === 0) {
        return 1;
      }

      return sum / n;
    };

    $scope.openConfirmableModalDialog = function(template, arg, scope) {
      scope = scope === undefined ? $rootScope : scope;

      return $uibModal.open({
        templateUrl: template,
        controller: 'ConfirmableDialogCtrl',
        backdrop: 'static',
        keyboard: false,
        scope: scope,
        resolve: {
          arg: function () {
            return arg;
          }
        }
      });
    };

    //////////////////////////////////////////////////////////////////

    $scope.$on("$locationChangeStart", function(event, next) {
      next = next.substring($location.absUrl().length - $location.url().length);
      if ($rootScope.forcedLocation && next !== $rootScope.forcedLocation) {
        event.preventDefault();
      }
    });

    /* eslint-disable no-unused-vars */
    $scope.$on("$routeChangeStart", function(event, next) {
    /* eslint-enable no-unused-vars */
      $scope.route_check();

      var path = $location.path();
      var embedded = '/embedded/';

      if ($location.path().substr(0, embedded.length) === embedded) {
        $rootScope.embedded = true;
        var search = $location.search();
        if (Object.keys(search).length === 0) {
          $location.path(path.replace("/embedded/", "/"));
          $location.search("embedded=true");
        } else {
          $location.url($location.url().replace("/embedded/", "/") + "&embedded=true");
        }
      }
    });

    /* eslint-disable no-unused-vars */
    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
    /* eslint-enable no-unused-vars */
      if (current.$$route) {
        $rootScope.successes = [];
        $rootScope.errors = [];
        $scope.header_title = current.$$route.header_title;
        $scope.header_subtitle = current.$$route.header_subtitle;
        $scope.set_title();
      }
    });

    $scope.$on("REFRESH", function() {
      $scope.reload();
    });

    $scope.$watch(function () {
      return Authentication.session;
    }, function () {
      $scope.session = Authentication.session;
    });

    $rootScope.keypress = function(e) {
       if (((e.which || e.keyCode) === 116) || /* F5 */
           ((e.which || e.keyCode) === 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */
         e.preventDefault();
         $scope.$emit("REFRESH");
       }
    };

    $scope.init();
  }
]).
controller('ModalCtrl', ['$scope', 
  function($scope, $uibModalInstance, error) {
    $scope.error = error;
    $scope.seconds = error.arguments[0];
}]).
controller('DisableEncryptionCtrl', ['$scope', '$uibModalInstance', function($scope, $uibModalInstance){
    $scope.close = function() {
      $uibModalInstance.close(false);
    };

    $scope.no = function() {
      $uibModalInstance.close(false);
    };

    $scope.ok = function() {
      $uibModalInstance.close(true);
    };
}]).
controller('ConfirmableDialogCtrl', ['$scope', '$uibModalInstance', 'arg', function($scope, $uibModalInstance, arg) {
  $scope.arg = arg;

  $scope.ok = function (result) {
    $uibModalInstance.close(result);
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss('cancel');
  };
}]);
