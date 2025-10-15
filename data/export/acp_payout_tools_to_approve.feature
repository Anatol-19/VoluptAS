@feature
Feature: ACP to Approve
  
  Автоматически сгенерированная feature для acp.payout_tools.to_approve
  
  Functional ID: acp.payout_tools.to_approve
  Module: ACP
  Epic: ACP
  Responsible QA: Максим
  Responsible Dev: N/A

  Background:
    Given модуль "ACP" доступен
    And эпик "ACP" инициализирован


  Scenario: Базовая функциональность ACP to Approve
    Given пользователь авторизован
    When пользователь использует "ACP to Approve"
    Then функционал работает корректно
    And нет ошибок
