'use strict';

function contains(collection, target) {
    var containsTarget = !1;
    return (collection.some(function(object) {
        return object === target ? (containsTarget = !0, !0) : void 0;
    }), containsTarget);
}

function find(collection, properties) {
    var target;
    return (collection.some(function(object) {
        var hasAllSameProperties = !0;
        return (Object.keys(properties).forEach(function(key) {
            object[key] !== properties[key] && (hasAllSameProperties = !1);
        }), hasAllSameProperties ? (target = object, !0) : void 0);
    }), target);
}

function findIndex(collection, properties) {
    var index = -1,
        counter = -1;
    return (collection.some(function(object) {
        var hasAllSameProperties = !0;
        return (counter += 1, Object.keys(properties).forEach(function(key) {
            object[key] !== properties[key] && (hasAllSameProperties = !1);
        }), hasAllSameProperties ? (index = counter, !0) : void 0);
    }), index);
}
var directiveModule = angular.module('angularjs-dropdown-multiselect', []);
directiveModule.directive('mfDropdownStaticInclude', ['$compile', function($compile) {
    return function(scope, element, attrs) {
        var template = attrs.mfDropdownStaticInclude,
            contents = element.html(template).contents();
        $compile(contents)(scope);
    };
}]), directiveModule.directive('ngDropdownMultiselect', ['$filter', '$document', '$compile', '$parse', function($filter, $document, $compile, $parse) {
    return {
        restrict: 'AE',
        scope: {
            selectedModel: '=',
            options: '=',
            extraSettings: '=',
            events: '=',
            searchFilter: '=?',
            translationTexts: '=',
            groupBy: '@',
            disabled: '='
        },
        template: function(element, attrs) {
            var checkboxes = attrs.checkboxes ? !0 : !1,
                groups = attrs.groupBy ? !0 : !1,
                template = "<div class='multiselect-parent btn-group dropdown-multiselect' ng-class='{open: open}'>";
            template += "<button ng-disabled='disabled' type='button' class='dropdownpadding dropdown noHover' ng-class='settings.buttonClasses' ng-click='toggleDropdown()'><i class='fa fa-filter'></i></button>", template += '<ul class=\'dropdown-menu dropdown-menu-form\' ng-if=\'open\' ng-style=\'{display: open ? "block" : "none", height : settings.scrollable ? settings.scrollableHeight : "auto", overflow: "auto" }\' >', template += "<li ng-if='settings.showCheckAll && settings.selectionLimit !== 1'><a ng-keydown='keyDownLink($event)' data-ng-click='selectAll()' tabindex='-1' id='selectAll'><span class='fa fa-square-check'></span>  {{texts.checkAll}}</a>", template += "<li ng-if='settings.showUncheckAll'><a ng-keydown='keyDownLink($event)' data-ng-click='deselectAll();' tabindex='-1' id='deselectAll'><span class='glyphicon glyphicon-remove'></span>   {{texts.uncheckAll}}</a></li>", template += "<li ng-if='settings.selectByGroups && ((settings.showCheckAll && settings.selectionLimit > 0) || settings.showUncheckAll)' class='divider'></li>", template += "<li ng-if='settings.selectByGroups && ((settings.showCheckAll && settings.selectionLimit > 0) || settings.showUncheckAll)' class='divider'></li>", template += "<li ng-repeat='currentGroup in settings.selectByGroups track by $index' ng-click='selectCurrentGroup(currentGroup)'><a ng-class='{\"dropdown-selected-group\": selectedGroup === currentGroup}' tabindex='-1'>{{::texts.selectGroup}} {{::getGroupLabel(currentGroup)}}</a></li>", template += "<li ng-if='settings.selectByGroups && settings.showEnableSearchButton' class='divider'></li>", template += "<li ng-if='settings.showEnableSearchButton && settings.enableSearch'><a ng-keydown='keyDownLink($event); keyDownToggleSearch();' ng-click='toggleSearch($event);' tabindex='-1'>{{texts.disableSearch}}</a></li>", template += "<li ng-if='settings.showEnableSearchButton && !settings.enableSearch'><a ng-keydown='keyDownLink($event); keyDownToggleSearch();' ng-click='toggleSearch($event);' tabindex='-1'>{{texts.enableSearch}}</a></li>", template += "<li ng-if='(settings.showCheckAll && settings.selectionLimit > 0) || settings.showUncheckAll || settings.showEnableSearchButton' class='divider'></li>", template += "<li ng-if='settings.enableSearch'><div class='dropdown-header'><input type='text' class='form-control searchField' ng-keydown='keyDownSearchDefault($event); keyDownSearch($event, input.searchFilter);' ng-style='{width: \"100%\"}' ng-model='input.searchFilter' placeholder='{{texts.searchPlaceholder}}' /></li>", template += "<li ng-if='settings.enableSearch' class='divider'></li>", groups ? (template += "<li ng-repeat-start='option in orderedItems | filter:getFilter(input.searchFilter)' ng-show='getPropertyForObject(option, settings.groupBy) !== getPropertyForObject(orderedItems[$index - 1], settings.groupBy)' role='presentation' class='dropdown-header'>{{ getGroupLabel(getPropertyForObject(option, settings.groupBy)) }}</li>", template += "<li ng-class='{\"active\": isChecked(getPropertyForObject(option,settings.idProp)) && settings.styleActive}' ng-repeat-end role='presentation'>") : template += "<li class='dropdown-items-container' ng-class='{\"active\": isChecked(getPropertyForObject(option,settings.idProp)) && settings.styleActive}' role='presentation' ng-repeat='option in options | filter:getFilter(input.searchFilter)'>", template += "<a class='dropdown-items-sub-container' ng-keydown='option.disabled || keyDownLink($event)' role='menuitem' class='option' tabindex='-1' ng-click='option.disabled || setSelectedItem(getPropertyForObject(option,settings.idProp), false, true)' ng-disabled='option.disabled'>", template += checkboxes ? "<div class='checkbox'><label><input class='checkboxInput' type='checkbox' ng-click='checkboxClick($event, getPropertyForObject(option,settings.idProp))' ng-checked='isChecked(getPropertyForObject(option,settings.idProp))' /> <span mf-dropdown-static-include='{{settings.template}}'></div></label></span></a>" : "<span data-ng-class='{\"fa-regular fa-square\": isChecked(getPropertyForObject(option,settings.idProp))}'> </span><span data-ng-class='{\"fa-regular fa-square-check\": isNotChecked(getPropertyForObject(option,settings.idProp))}'> </span> <span class='dropdown-items' mf-dropdown-static-include='{{settings.template}}'></span></a>", template += '</li>', template += "<li class='divider' ng-show='settings.selectionLimit > 1'></li>", template += "<li role='presentation' ng-show='settings.selectionLimit > 1'><a role='menuitem'>{{selectedModel.length}} {{texts.selectionOf}} {{settings.selectionLimit}} {{texts.selectionCount}}</a></li>", template += '</ul>', template += '</div>', element.html(template)
        },
        getPropertyForObject_uncheck: function(){
        }
        ,link: function($scope, $element, $attrs) {
            function getFindObj(id) {
                var findObj = {};
                return ('' === $scope.settings.externalIdProp ? findObj[$scope.settings.idProp] = id : findObj[$scope.settings.externalIdProp] = id, findObj);
            }

            function clearObject(object) {
                for (var prop in object) delete object[prop]
            }
            var $dropdownTrigger = $element.children()[0];
            $scope.toggleDropdown = function() {
                $scope.open ? $scope.close() : $scope.open = !0, $scope.settings.keyboardControls && $scope.open && (1 === $scope.settings.selectionLimit && $scope.settings.enableSearch ? setTimeout(function() {
                    angular.element($element)[0].querySelector('.searchField').focus()
                }, 0) : setTimeout(function() {
                    angular.element($element)[0].querySelector('.option').focus()
                }, 0))
            }, $scope.checkboxClick = function($event, id) {
                $scope.setSelectedItem(id, !1, !0), $event.stopImmediatePropagation()
            }, $scope.externalEvents = {
                onItemSelect: angular.noop,
                onItemDeselect: angular.noop,
                onSelectAll: angular.noop,
                onDeselectAll: angular.noop,
                onInitDone: angular.noop,
                onMaxSelectionReached: angular.noop,
                onSelectionChanged: angular.noop,
                onClose: angular.noop
            }, $scope.settings = {
                dynamicTitle: 0,
                scrollable: !1,
                scrollableHeight: '300px',
                closeOnBlur: !0,
                displayProp: 'label',
                idProp: 'id',
                externalIdProp: 'id',
                enableSearch: !1,
                selectionLimit: 0,
                showCheckAll: 0,
                showUncheckAll: 0,
                showEnableSearchButton: !1,
                closeOnSelect: !1,
                buttonClasses: 'btn btn-default',
                closeOnDeselect: !1,
                groupBy: $attrs.groupBy || void 0,
                groupByTextProvider: null,
                smartButtonMaxItems: 0,
                smartButtonTextConverter: angular.noop,
                styleActive: 0,
                keyboardControls: !1,
                template: '{{getPropertyForObject(option, settings.displayProp)}}',
                searchField: '$'
            }, $scope.texts = {
                checkAll: 'Check All',
                uncheckAll: 'Uncheck All',
                selectionCount: 'checked',
                selectionOf: '/',
                searchPlaceholder: $filter('translate')('Search')+'...',
                buttonDefaultText: '⧩',
                dynamicButtonTextSuffix: 'checked',
                disableSearch: 'Disable search',
                enableSearch: 'Enable search',
                selectGroup: 'Select all:'
            }, $scope.input = {
                searchFilter: $scope.searchFilter || ''
            }, angular.isDefined($scope.settings.groupBy) && $scope.$watch('options', function(newValue) {
                angular.isDefined(newValue) && ($scope.orderedItems = $filter('orderBy')(newValue, $scope.settings.groupBy))
            }), $scope.$watch('selectedModel', function(newValue) {
                Array.isArray(newValue) ? $scope.singleSelection = !1 : $scope.singleSelection = !0
            }), $scope.close = function() {
                $scope.open = !1, $scope.externalEvents.onClose()
            }, $scope.selectCurrentGroup = function(currentGroup) {
                $scope.selectedModel.splice(0, $scope.selectedModel.length), $scope.orderedItems && $scope.orderedItems.forEach(function(item) {
                    item[$scope.groupBy] === currentGroup && $scope.setSelectedItem($scope.getPropertyForObject(item, $scope.settings.idProp), !1, !1)
                }), $scope.externalEvents.onSelectionChanged()
            }, angular.extend($scope.settings, $scope.extraSettings || []), angular.extend($scope.externalEvents, $scope.events || []), angular.extend($scope.texts, $scope.translationTexts), $scope.singleSelection = 1 === $scope.settings.selectionLimit, $scope.singleSelection && angular.isArray($scope.selectedModel) && 0 === $scope.selectedModel.length && clearObject($scope.selectedModel), $scope.settings.closeOnBlur && $document.on('click', function(e) {
                if ($scope.open) {
                    for (var target = e.target.parentElement, parentFound = !1; angular.isDefined(target) && null !== target && !parentFound; ) {
                        target.className.split && contains(target.className.split(' '), 'multiselect-parent') && !parentFound && target === $dropdownTrigger && (parentFound = !0), target = target.parentElement;
                    }
                    parentFound || $scope.$apply(function() {
                        $scope.close()
                    })
                }
            }), $scope.getGroupLabel = function(groupValue) {
                return null !== $scope.settings.groupByTextProvider ? $scope.settings.groupByTextProvider(groupValue) : groupValue
            }, $scope.getButtonText = function() {
                if ($scope.settings.dynamicTitle && ($scope.selectedModel.length > 0 || angular.isObject($scope.selectedModel) && Object.keys($scope.selectedModel).length > 0)) {
                    if ($scope.settings.smartButtonMaxItems > 0) {
                        var itemsText = [];
                        return (angular.forEach($scope.options, function(optionItem) {
                            if ($scope.isChecked($scope.getPropertyForObject(optionItem, $scope.settings.idProp))) {
                                var displayText = $scope.getPropertyForObject(optionItem, $scope.settings.displayProp),
                                    converterResponse = $scope.settings.smartButtonTextConverter(displayText, optionItem);
                                itemsText.push(converterResponse ? converterResponse : displayText)
                            }
                        }), $scope.selectedModel.length > $scope.settings.smartButtonMaxItems && (itemsText = itemsText.slice(0, $scope.settings.smartButtonMaxItems), itemsText.push('...')), itemsText.join(', '))
                    }
                    var totalSelected;
                    return (totalSelected = $scope.singleSelection ? null !== $scope.selectedModel && angular.isDefined($scope.selectedModel[$scope.settings.idProp]) ? 1 : 0 : angular.isDefined($scope.selectedModel) ? $scope.selectedModel.length : 0, 0 === totalSelected ? $scope.texts.buttonDefaultText : totalSelected + ' ' + $scope.texts.dynamicButtonTextSuffix)
                }
                return $scope.texts.buttonDefaultText
            }, $scope.getPropertyForObject = function(object, property) {
                return angular.isDefined(object) && object.hasOwnProperty(property) ? object[property] : ''
            }, $scope.selectAll = function() {
                var searchResult;
                $scope.deselectAll(!0), $scope.externalEvents.onSelectAll(), searchResult = $filter('filter')($scope.options, $scope.getFilter($scope.input.searchFilter)), angular.forEach(searchResult, function(value) {
                    $scope.setSelectedItem(value[$scope.settings.idProp], !0, !1)
                }), $scope.externalEvents.onSelectionChanged(), $scope.selectedGroup = null;
            }, $scope.deselectAll = function(dontSendEvent) {
                dontSendEvent = dontSendEvent || !1, dontSendEvent || $scope.externalEvents.onDeselectAll(), $scope.singleSelection ? clearObject($scope.selectedModel) : $scope.selectedModel.splice(0, $scope.selectedModel.length), dontSendEvent || $scope.externalEvents.onSelectionChanged(), $scope.selectedGroup = null
            }, $scope.setSelectedItem = function(id, dontRemove, fireSelectionChange) {
                var findObj = getFindObj(id),
                    finalObj = null;
                if ((finalObj = '' === $scope.settings.externalIdProp ? find($scope.options, findObj) : findObj, $scope.singleSelection)) {
                    clearObject($scope.selectedModel), angular.extend($scope.selectedModel, finalObj), $scope.externalEvents.onItemSelect(finalObj), ($scope.settings.closeOnSelect || $scope.settings.closeOnDeselect) && $scope.close();
                } else {
                    dontRemove = dontRemove || !1;
                    var exists = -1 !== findIndex($scope.selectedModel, findObj);
                    !dontRemove && exists ? ($scope.selectedModel.splice(findIndex($scope.selectedModel, findObj), 1), $scope.externalEvents.onItemDeselect(findObj), $scope.settings.closeOnDeselect && $scope.close()) : !exists && (0 === $scope.settings.selectionLimit || $scope.selectedModel.length < $scope.settings.selectionLimit) && ($scope.selectedModel.push(finalObj), $scope.externalEvents.onItemSelect(finalObj), $scope.settings.closeOnSelect && $scope.close(), $scope.settings.selectionLimit > 0 && $scope.selectedModel.length === $scope.settings.selectionLimit && $scope.externalEvents.onMaxSelectionReached())
                }
                fireSelectionChange && $scope.externalEvents.onSelectionChanged(), $scope.selectedGroup = null;
            }, $scope.isNotChecked = function(id) {
                return ($scope.singleSelection ? null !== $scope.selectedModel && angular.isDefined($scope.selectedModel[$scope.settings.idProp]) && $scope.selectedModel[$scope.settings.idProp] === getFindObj(id)[$scope.settings.idProp] : -1 !== findIndex($scope.selectedModel, getFindObj(id)))
            }, $scope.isChecked = function(id) {
                return !($scope.singleSelection ? null !== $scope.selectedModel && angular.isDefined($scope.selectedModel[$scope.settings.idProp]) && $scope.selectedModel[$scope.settings.idProp] === getFindObj(id)[$scope.settings.idProp] : -1 !== findIndex($scope.selectedModel, getFindObj(id)))
            }, $scope.externalEvents.onInitDone(), $scope.keyDownLink = function(event) {
                var nextOption, sourceScope = angular.element(event.target).scope(),
                    parent = event.target.parentNode;
                if ($scope.settings.keyboardControls) {
                    if (13 === event.keyCode || 32 === event.keyCode) {
                        event.preventDefault(), sourceScope.option ? $scope.setSelectedItem($scope.getPropertyForObject(sourceScope.option, $scope.settings.idProp), !1, !0) : 'deselectAll' === event.target.id ? $scope.deselectAll() : 'selectAll' === event.target.id && $scope.selectAll();
                    } else if (38 === event.keyCode) {
                    for (event.preventDefault(), parent.previousElementSibling && (nextOption = parent.previousElementSibling.querySelector('a') || parent.previousElementSibling.querySelector('input')); !nextOption && parent; ) {
                        parent = parent.previousElementSibling, parent && (nextOption = parent.querySelector('a') || parent.querySelector('input'));
                    }
                    nextOption && nextOption.focus();
                } else if (40 === event.keyCode) {
                    for (event.preventDefault(), parent.nextElementSibling && (nextOption = parent.nextElementSibling.querySelector('a') || parent.nextElementSibling.querySelector('input')); !nextOption && parent; ) {
                        parent = parent.nextElementSibling, parent && (nextOption = parent.querySelector('a') || parent.querySelector('input'));
                    }
                    nextOption && nextOption.focus();
                } else {
                        27 === event.keyCode && (event.preventDefault(), $scope.toggleDropdown());
                    }
                }
            }, $scope.keyDownSearchDefault = function(event) {
                var nextOption, parent = event.target.parentNode.parentNode;
                if ($scope.settings.keyboardControls) {
                    if (9 === event.keyCode || 40 === event.keyCode) {
                        event.preventDefault(), setTimeout(function() {
                            angular.element($element)[0].querySelector('.option').focus();
                        }, 0);
                    } else if (38 === event.keyCode) {
                    for (event.preventDefault(), parent.previousElementSibling && (nextOption = parent.previousElementSibling.querySelector('a') || parent.previousElementSibling.querySelector('input')); !nextOption && parent; ) {
                        parent = parent.previousElementSibling, parent && (nextOption = parent.querySelector('a') || parent.querySelector('input'));
                    }
                    nextOption && nextOption.focus();
                } else {
                        27 === event.keyCode && (event.preventDefault(), $scope.toggleDropdown());
                    }
                }
            }, $scope.keyDownSearch = function(event, searchFilter) {
                var searchResult;
                $scope.settings.keyboardControls && 13 === event.keyCode && (1 === $scope.settings.selectionLimit && $scope.settings.enableSearch ? (searchResult = $filter('filter')($scope.options, $scope.getFilter(searchFilter)), 1 === searchResult.length && $scope.setSelectedItem($scope.getPropertyForObject(searchResult[0], $scope.settings.idProp), !1, !0)) : $scope.settings.enableSearch && $scope.selectAll())
            }, $scope.getFilter = function(searchFilter) {
                var filter = {};
                return (filter[$scope.settings.searchField] = searchFilter, filter);
            }, $scope.toggleSearch = function($event) {
                $event && $event.stopPropagation(), $scope.settings.enableSearch = !$scope.settings.enableSearch, $scope.settings.enableSearch || ($scope.input.searchFilter = '')
            }, $scope.keyDownToggleSearch = function() {
                $scope.settings.keyboardControls && 13 === event.keyCode && ($scope.toggleSearch(), $scope.settings.enableSearch ? setTimeout(function() {
                    angular.element($element)[0].querySelector('.searchField').focus();
                }, 0) : angular.element($element)[0].querySelector('.option').focus())
            }
        }
    }
}]);