@api @feature
Feature: [Feature]: change password
  
  Автоматически сгенерированная feature для front.dashboard.change_password
  
  Functional ID: front.dashboard.change_password
  Module: FRONT
  Epic: Account Managment
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Account Managment" инициализирован


  Scenario: Базовая функциональность [Feature]: change password
    Given пользователь авторизован
    When пользователь использует "[Feature]: change password"
    Then функционал работает корректно
    And нет ошибок
