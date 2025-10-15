@api @feature
Feature: [Feature]: Auth Member by Username
  
  Автоматически сгенерированная feature для front.auth.member.username
  
  Functional ID: front.auth.member.username
  Module: FRONT
  Epic: Auth
  Responsible QA: Степан
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Auth Member by Username
    Given пользователь авторизован
    When пользователь использует "[Feature]: Auth Member by Username"
    Then функционал работает корректно
    And нет ошибок
