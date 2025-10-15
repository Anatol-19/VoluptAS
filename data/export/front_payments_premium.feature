@ux _cx @feature
Feature: [Feature]: Join Now - Premium
  
  Функционал отображения прайсов мемберам по ожидаемой логике и настрйокам
  
  Functional ID: front.payments.premium
  Module: FRONT
  Epic: Payments
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Payments" инициализирован


  Scenario: Базовая функциональность [Feature]: Join Now - Premium
    Given пользователь авторизован
    When пользователь использует "[Feature]: Join Now - Premium"
    Then функционал работает корректно
    And нет ошибок
