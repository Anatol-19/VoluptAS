@api @feature
Feature: [Feature]: change username
  
  Автоматически сгенерированная feature для front.dashboard.change_username
  
  Functional ID: front.dashboard.change_username
  Module: FRONT
  Epic: Account Managment
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Account Managment" инициализирован


  Scenario: Базовая функциональность [Feature]: change username
    Given пользователь авторизован
    When пользователь использует "[Feature]: change username"
    Then функционал работает корректно
    And нет ошибок
