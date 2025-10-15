@api @feature
Feature: [Feature]: Emails: Drop Carts
  
  Автоматически сгенерированная feature для vrb_web.email.drop_carts
  
  Functional ID: vrb_web.email.drop_carts
  Module: VRB WEB
  Epic: EMail
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "VRB WEB" доступен
    And эпик "EMail" инициализирован


  Scenario: Базовая функциональность [Feature]: Emails: Drop Carts
    Given пользователь авторизован
    When пользователь использует "[Feature]: Emails: Drop Carts"
    Then функционал работает корректно
    And нет ошибок
