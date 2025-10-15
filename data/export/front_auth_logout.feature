@api @feature
Feature: [Feature]: Log Out
  
  Автоматически сгенерированная feature для front.auth.logout
  
  Functional ID: front.auth.logout
  Module: FRONT
  Epic: Auth
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Log Out
    Given пользователь авторизован
    When пользователь использует "[Feature]: Log Out"
    Then функционал работает корректно
    And нет ошибок
