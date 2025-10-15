@ux _cx @feature
Feature: [Feature]: Main Page Content
  
  Авто модерацияя контента для главных блоков согласно настройкам в админке
  
  Functional ID: front.pages.main.UX
  Module: FRONT
  Epic: Main Page
  Responsible QA: Данил
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Main Page" инициализирован


  Scenario: Базовая функциональность [Feature]: Main Page Content
    Given пользователь авторизован
    When пользователь использует "[Feature]: Main Page Content"
    Then функционал работает корректно
    And нет ошибок
