@ux _cx @feature
Feature: [Page]: Premium Landing Page
  
  Соответствие поведение ожидаемому
  
  Functional ID: front.pages.premium
  Module: FRONT
  Epic: Payments
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Payments" инициализирован


  Scenario: Базовая функциональность [Page]: Premium Landing Page
    Given пользователь авторизован
    When пользователь использует "[Page]: Premium Landing Page"
    Then функционал работает корректно
    And нет ошибок
