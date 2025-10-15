@feature
Feature: ACP Payout History
  
  Автоматически сгенерированная feature для acp.payout_tools.history
  
  Functional ID: acp.payout_tools.history
  Module: ACP
  Epic: ACP
  Responsible QA: Максим
  Responsible Dev: N/A

  Background:
    Given модуль "ACP" доступен
    And эпик "ACP" инициализирован


  Scenario: Базовая функциональность ACP Payout History
    Given пользователь авторизован
    When пользователь использует "ACP Payout History"
    Then функционал работает корректно
    And нет ошибок
