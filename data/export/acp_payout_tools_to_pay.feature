@feature
Feature: ACP to Pay
  
  Автоматически сгенерированная feature для acp.payout_tools.to_pay
  
  Functional ID: acp.payout_tools.to_pay
  Module: ACP
  Epic: ACP
  Responsible QA: Максим
  Responsible Dev: N/A

  Background:
    Given модуль "ACP" доступен
    And эпик "ACP" инициализирован


  Scenario: Базовая функциональность ACP to Pay
    Given пользователь авторизован
    When пользователь использует "ACP to Pay"
    Then функционал работает корректно
    And нет ошибок
