@ux _cx @feature
Feature: Easy Cancel btn
  
  Автоматически сгенерированная feature для front.dashboard.easy_cancel.btn
  
  Functional ID: front.dashboard.easy_cancel.btn
  Module: FRONT
  Epic: EasyCancel
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "EasyCancel" инициализирован


  Scenario: Базовая функциональность Easy Cancel btn
    Given пользователь авторизован
    When пользователь использует "Easy Cancel btn"
    Then функционал работает корректно
    And нет ошибок
