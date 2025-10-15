@api @feature
Feature: [Feature]: Auth Member by Email
  
  Автоматически сгенерированная feature для front.auth.member.email
  
  Functional ID: front.auth.member.email
  Module: FRONT
  Epic: Auth
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Auth Member by Email
    Given пользователь авторизован
    When пользователь использует "[Feature]: Auth Member by Email"
    Then функционал работает корректно
    And нет ошибок
