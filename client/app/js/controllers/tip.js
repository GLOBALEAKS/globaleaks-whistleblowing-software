GLClient.controller('TipCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$uibModal', '$http', 'Authentication', 'RTip', 'WBTip', 'ReceiverPreferences', 'fieldUtilities',
  function($scope, $rootScope, $location, $route, $routeParams, $uibModal, $http, Authentication, RTip, WBTip, ReceiverPreferences, fieldUtilities) {
    $scope.tip_id = $routeParams.tip_id;
    $scope.target_file = '#';

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

    if (!$scope.session) {
      // FIXME: handle this applicationwide with somekind of state
      $scope.loginRedirect(true);
      return;
    }

    $scope.getAnswersEntries = function(entry) {
      if (entry === undefined) {
        return $scope.answers[$scope.field.id];
      }

      return entry[$scope.field.id];
    };

    $scope.extractSpecialTipFields = function(tip) {
      for (var i=tip.questionnaire.length - 1; i>=0; i--) {
        var step = tip.questionnaire[i];
        var j = step.children.length;
        while (j--) {
          if (step.children[j]['key'] === 'whistleblower_identity') {
            $scope.whistleblower_identity_field = step.children[j];
            step.children.splice(j, 1);
            $scope.fields = $scope.whistleblower_identity_field.children;
            $scope.rows = fieldUtilities.splitRows($scope.fields);
            $scope.field = $scope.whistleblower_identity_field;

            for (var k1 = 0; k1 < $scope.field.children.length; k1++) {
              var child = $scope.field.children[k1];
              $scope.answers[child.id] = [angular.copy(fieldUtilities.prepare_field_answers_structure(child))];
            }
          }
        }

        if ($scope.node.enable_experimental_features) {
          var filterNotTriggeredField = function(field, answers) {
            for(var k2=field.children.length - 1; k2>=0; k2--) {
              var f = field.children[k2];
              if (!$scope.isFieldTriggered(f, answers[f.id], $scope.tip.total_score)) {
                field.children.splice(k2, 1);
              } else {
                for (var k3=0; k2<answers[f.id].length; k3++) {
                  filterNotTriggeredField(f, answers[f.id]);
                }
              }
            }
          }

          if (!$scope.isStepTriggered(step, $scope.tip.answers, $scope.tip.total_score)) {
            tip.questionnaire.splice(i, 1);
          } else {
            for (var k4=0; k4<step.children.length; k4++) {
              var field = step.children[k4];
              for (var k5=0; k5<$scope.tip.answers[field.id].length; k5++) {
                filterNotTriggeredField(field, $scope.tip.answers[field.id][k5]);
              }
            }
          }
        }

      }
    };

    $scope.hasMultipleEntries = function(field_answer) {
      if (field_answer !== undefined) {
        return field_answer.length > 1;
      }

      return false;
    };

    $scope.filterFields = function(field) {
      return field.type !== 'fileupload';
    };

    $scope.filterReceivers = function(receiver) {
      return receiver.configuration !== 'hidden';
    };

    if ($scope.session.role === 'whistleblower') {
      $scope.fileupload_url = 'wbtip/upload';

      new WBTip(function(tip) {
        $scope.tip = tip;
        $scope.extractSpecialTipFields(tip);

        // FIXME: remove this variable that is now needed only to map wb_identity_field
        $scope.submission = tip;

        $scope.provideIdentityInformation = function(identity_field_id, identity_field_answers) {
          return $http.post('wbtip/' + $scope.tip.id + '/provideidentityinformation',
                            {'identity_field_id': identity_field_id, 'identity_field_answers': identity_field_answers}).
              success(function(){
                $route.reload();
              });
        };

        angular.forEach($scope.contexts, function(context){
          if (context.id === tip.context_id) {
            $scope.current_context = context;
          }
        });

        if (tip.receivers.length === 1 && tip.msg_receiver_selected === null) {
          tip.msg_receiver_selected = tip.msg_receivers_selector[0].key;
        }

        tip.updateMessages();

        $scope.$watch('tip.msg_receiver_selected', function (newVal, oldVal) {
          if (newVal && newVal !== oldVal) {
            if ($scope.tip) {
              $scope.tip.updateMessages();
            }
          }
        }, false);
      });

    } else if ($scope.session.role === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    
      new RTip({id: $scope.tip_id}, function(tip) {
        $scope.tip = tip;
        $scope.extractSpecialTipFields(tip);

        $scope.showEditLabelInput = $scope.tip.label === '';

        $scope.tip_unencrypted = false;
        angular.forEach(tip.receivers, function(receiver){
          if (receiver.pgp_key_status === 'disabled' && receiver.receiver_id !== tip.receiver_id) {
            $scope.tip_unencrypted = true;
          }
        });

        angular.forEach($scope.contexts, function(context){
          if (context.id === $scope.tip.context_id) {
            $scope.current_context = context;
          }
        });

      });
    } else {
      if($location.path() === '/status') {
        // whistleblower
        $location.path('/');
      } else {
        // receiver
        var search = 'src=' + $location.path();
        $location.path('/login');
        $location.search(search);
      }
    }

    $scope.editLabel = function() {
      $scope.showEditLabelInput = true;
    };

    $scope.updateLabel = function(label) {
      $scope.tip.updateLabel(label);
      $scope.showEditLabelInput = false;
    };

    $scope.allowWhistleblowerToComment = function() {
      return $scope.tip.setVar('enable_two_way_comments', true);
    };

    $scope.denyWhistleblowerToComment = function() {
      return $scope.tip.setVar('enable_two_way_comments', false);
    };

    $scope.allowWhistleblowerToMessage = function() {
      return $scope.tip.setVar('enable_two_way_messages', true);
    };

    $scope.denyWhistleblowerToMessage = function() {
      return $scope.tip.setVar('enable_two_way_messages', false);
    };

    $scope.allowWhistleblowerToAttachFiles = function() {
      return $scope.tip.setVar('enable_attachments', true);
    };

    $scope.denyWhistleblowerToAttachFiles = function() {
      return $scope.tip.setVar('enable_attachments', false);
    };

    $scope.newComment = function() {
      $scope.tip.newComment($scope.tip.newCommentContent);
      $scope.tip.newCommentContent = '';
    };

    $scope.newMessage = function() {
      $scope.tip.newMessage($scope.tip.newMessageContent);
      $scope.tip.newMessageContent = '';
    };

    $scope.tip_notify = function(enable) {
      $scope.tip.setVar('enable_notifications', enable);
    };

    $scope.tip_delete = function () {
      $uibModal.open({
        templateUrl: 'views/partials/tip_operation_delete.html',
        controller: 'TipOperationsCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          },
          operation: function () {
            return 'delete';
          }
        }
      });
    };

    $scope.tip_postpone = function () {
      $uibModal.open({
        templateUrl: 'views/partials/tip_operation_postpone.html',
        controller: 'TipOperationsCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          },
          operation: function () {
            return 'postpone';
          }
        }
      });
    };

    $scope.file_identity_access_request = function () {
      $uibModal.open({
        templateUrl: 'views/partials/tip_operation_file_identity_access_request.html',
        controller: 'IdentityAccessRequestCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          }
        }
      });
    };
}]).
controller('TipOperationsCtrl',
  ['$scope', '$http', '$route', '$location', '$uibModalInstance', 'RTip', 'tip', 'operation',
   function ($scope, $http, $route, $location, $uibModalInstance, Tip, tip, operation) {
  $scope.tip = tip;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    if ($scope.operation === 'postpone') {
      var req = {
        'operation': 'postpone',
        'args': {}
      };

      return $http({method: 'PUT', url: '/rtip/' + tip.id, data: req}).success(function () {
        $route.reload();
      });
    } else if ($scope.operation === 'delete') {
      return $http({method: 'DELETE', url: '/rtip/' + $scope.tip.id, data:{}}).
        success(function() {
          $location.url('/receiver/tips');
          $route.reload();
        });
    }
  };
}]).
controller('IdentityAccessRequestCtrl',
  ['$scope', '$http', '$route', '$uibModalInstance', 'tip',
   function ($scope, $http, $route, $uibModalInstance, tip) {
  $scope.tip = tip;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    return $http.post('/rtip/' + tip.id + '/identityaccessrequests', {'request_motivation': $scope.request_motivation}).
        success(function(){
          $route.reload();
        });
  };
}]);
