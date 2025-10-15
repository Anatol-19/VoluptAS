@api @feature
Feature: Account JWT Auth
  
  Автоматически сгенерированная feature для vrb_web.account.jwt
  
  Functional ID: vrb_web.account.jwt
  Module: VRB WEB
  Epic: Authorization
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "VRB WEB" доступен
    And эпик "Authorization" инициализирован


  Scenario: Базовая функциональность Account JWT Auth
    Given пользователь авторизован
    When пользователь использует "Account JWT Auth"
    Then функционал работает корректно
    And нет ошибок
