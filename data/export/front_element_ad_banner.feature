@ux _cx @feature
Feature: [Feature]: Ad Banner
  
  Автоматически сгенерированная feature для front.element.ad_banner
  
  Functional ID: front.element.ad_banner
  Module: FRONT
  Epic: Announcements
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Announcements" инициализирован


  Scenario: Базовая функциональность [Feature]: Ad Banner
    Given пользователь авторизован
    When пользователь использует "[Feature]: Ad Banner"
    Then функционал работает корректно
    And нет ошибок
