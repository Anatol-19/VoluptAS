@ux _cx @feature
Feature: [Feature]: Value Pop-Up
  
  Автоматически сгенерированная feature для front.element.value_popup
  
  Functional ID: front.element.value_popup
  Module: FRONT
  Epic: Announcements
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Announcements" инициализирован


  Scenario: Базовая функциональность [Feature]: Value Pop-Up
    Given пользователь авторизован
    When пользователь использует "[Feature]: Value Pop-Up"
    Then функционал работает корректно
    And нет ошибок
