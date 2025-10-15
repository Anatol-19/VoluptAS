@ux _cx @feature
Feature: [Feature]: Header Bar
  
  Автоматически сгенерированная feature для front.element.header_bar
  
  Functional ID: front.element.header_bar
  Module: FRONT
  Epic: Announcements
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Announcements" инициализирован


  Scenario: Базовая функциональность [Feature]: Header Bar
    Given пользователь авторизован
    When пользователь использует "[Feature]: Header Bar"
    Then функционал работает корректно
    And нет ошибок
