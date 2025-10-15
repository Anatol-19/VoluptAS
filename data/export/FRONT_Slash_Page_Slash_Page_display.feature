@ui @feature
Feature: [Feature]: Splash Page
  
  Перекрытие контента по любому роуту сплешом
  
  Functional ID: FRONT.Slash_Page.Slash_Page_display
  Module: FRONT
  Epic: Slash Page
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Slash Page" инициализирован


  Scenario: Базовая функциональность [Feature]: Splash Page
    Given пользователь авторизован
    When пользователь использует "[Feature]: Splash Page"
    Then функционал работает корректно
    And нет ошибок
