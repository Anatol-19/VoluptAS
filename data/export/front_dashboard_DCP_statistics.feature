@workflow @feature
Feature: Dashboard: Creator Stats
  
  Аналитика хитов и выплат
  
  Functional ID: front.dashboard.DCP.statistics
  Module: FRONT
  Epic: Creators DCP
  Responsible QA: Максим
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Creators DCP" инициализирован


  Scenario: Базовая функциональность Dashboard: Creator Stats
    Given пользователь авторизован
    When пользователь использует "Dashboard: Creator Stats"
    Then функционал работает корректно
    And нет ошибок
