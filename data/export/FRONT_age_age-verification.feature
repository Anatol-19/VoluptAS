@ux _cx @feature
Feature: [Feature]: Age Verification
  
  Выход на верификацию для Active
  
  Functional ID: FRONT.age.age-verification
  Module: FRONT
  Epic: age
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "age" инициализирован


  Scenario: Базовая функциональность [Feature]: Age Verification
    Given пользователь авторизован
    When пользователь использует "[Feature]: Age Verification"
    Then функционал работает корректно
    And нет ошибок
