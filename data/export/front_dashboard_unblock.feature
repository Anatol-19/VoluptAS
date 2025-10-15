@api @feature
Feature: [Feature]: unblock / block
  
  Автоматически сгенерированная feature для front.dashboard.unblock
  
  Functional ID: front.dashboard.unblock
  Module: FRONT
  Epic: Account Managment
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Account Managment" инициализирован


  Scenario: Базовая функциональность [Feature]: unblock / block
    Given пользователь авторизован
    When пользователь использует "[Feature]: unblock / block"
    Then функционал работает корректно
    And нет ошибок
