@api @feature
Feature: Easy Cancel - Cancel recurrent
  
  Автоматически сгенерированная feature для front.dashboard.easy_cancel.cancel
  
  Functional ID: front.dashboard.easy_cancel.cancel
  Module: FRONT
  Epic: EasyCancel
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "EasyCancel" инициализирован


  Scenario: Базовая функциональность Easy Cancel - Cancel recurrent
    Given пользователь авторизован
    When пользователь использует "Easy Cancel - Cancel recurrent"
    Then функционал работает корректно
    And нет ошибок
