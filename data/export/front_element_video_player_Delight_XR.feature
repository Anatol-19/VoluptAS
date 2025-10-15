@integration @feature
Feature: [Feature]:
  
  Автоматически сгенерированная feature для front.element.video_player.Delight_XR
  
  Functional ID: front.element.video_player.Delight_XR
  Module: FRONT
  Epic: video player
  Responsible QA: Данил
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "video player" инициализирован


  Scenario: Базовая функциональность [Feature]:
    Given пользователь авторизован
    When пользователь использует "[Feature]:"
    Then функционал работает корректно
    And нет ошибок
