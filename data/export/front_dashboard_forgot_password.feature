@api @feature
Feature: [Feature]: Fogod password
  
  Автоматически сгенерированная feature для front.dashboard.forgot_password
  
  Functional ID: front.dashboard.forgot_password
  Module: FRONT
  Epic: Account Managment
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Account Managment" инициализирован


  Scenario: Базовая функциональность [Feature]: Fogod password
    Given пользователь авторизован
    When пользователь использует "[Feature]: Fogod password"
    Then функционал работает корректно
    And нет ошибок
