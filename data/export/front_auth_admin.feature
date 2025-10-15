@api @feature
Feature: [Feature]: Admin Login
  
  Автоматически сгенерированная feature для front.auth.admin
  
  Functional ID: front.auth.admin
  Module: FRONT
  Epic: Auth
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Admin Login
    Given пользователь авторизован
    When пользователь использует "[Feature]: Admin Login"
    Then функционал работает корректно
    And нет ошибок
