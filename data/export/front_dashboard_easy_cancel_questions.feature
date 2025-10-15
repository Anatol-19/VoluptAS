@ux _cx @feature
Feature: Easy Cancel Вопросы при отмене
  
  Автоматически сгенерированная feature для front.dashboard.easy_cancel.questions
  
  Functional ID: front.dashboard.easy_cancel.questions
  Module: FRONT
  Epic: EasyCancel
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "EasyCancel" инициализирован


  Scenario: Базовая функциональность Easy Cancel Вопросы при отмене
    Given пользователь авторизован
    When пользователь использует "Easy Cancel Вопросы при отмене"
    Then функционал работает корректно
    And нет ошибок
