@ux _cx @feature
Feature: [Feature]: Soft Page
  
  Подмена контента на Soft режим для Free
  
  Functional ID: FRONT.age.soft_page
  Module: FRONT
  Epic: age
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "age" инициализирован


  Scenario: Базовая функциональность [Feature]: Soft Page
    Given пользователь авторизован
    When пользователь использует "[Feature]: Soft Page"
    Then функционал работает корректно
    And нет ошибок
