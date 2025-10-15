@api @feature
Feature: [Feature]: Refresh Token
  
  Автоматически сгенерированная feature для front.auth.refresh_token
  
  Functional ID: front.auth.refresh_token
  Module: FRONT
  Epic: Auth
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Refresh Token
    Given пользователь авторизован
    When пользователь использует "[Feature]: Refresh Token"
    Then функционал работает корректно
    And нет ошибок
