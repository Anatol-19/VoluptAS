@ux _cx @feature
Feature: [Feature]:  Announcement Slider
  
  Автоматически сгенерированная feature для front.element.announcement_slider
  
  Functional ID: front.element.announcement_slider
  Module: FRONT
  Epic: Announcements
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Announcements" инициализирован


  Scenario: Базовая функциональность [Feature]:  Announcement Slider
    Given пользователь авторизован
    When пользователь использует "[Feature]:  Announcement Slider"
    Then функционал работает корректно
    And нет ошибок
