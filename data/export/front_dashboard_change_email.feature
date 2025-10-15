@api @feature
Feature: [Feature]: Change Email
  
  Автоматически сгенерированная feature для front.dashboard.change_email
  
  Functional ID: front.dashboard.change_email
  Module: FRONT
  Epic: Account Managment
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Account Managment" инициализирован


  Scenario: Базовая функциональность [Feature]: Change Email
    Given пользователь авторизован
    When пользователь использует "[Feature]: Change Email"
    Then функционал работает корректно
    And нет ошибок
