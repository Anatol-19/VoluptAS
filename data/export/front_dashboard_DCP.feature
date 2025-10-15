@feature
Feature: Dashboard: Creators
  
  Формы и пр
  
  Functional ID: front.dashboard.DCP
  Module: FRONT
  Epic: Creators DCP
  Responsible QA: N/A
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Creators DCP" инициализирован


  Scenario: Базовая функциональность Dashboard: Creators
    Given пользователь авторизован
    When пользователь использует "Dashboard: Creators"
    Then функционал работает корректно
    And нет ошибок
