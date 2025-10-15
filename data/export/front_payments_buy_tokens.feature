@ux _cx @feature
Feature: [Feature]: Buy Tokens
  
  Соответствие поведение ожидаемому
  
  Functional ID: front.payments.buy_tokens
  Module: FRONT
  Epic: Payments
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Payments" инициализирован


  Scenario: Базовая функциональность [Feature]: Buy Tokens
    Given пользователь авторизован
    When пользователь использует "[Feature]: Buy Tokens"
    Then функционал работает корректно
    And нет ошибок
