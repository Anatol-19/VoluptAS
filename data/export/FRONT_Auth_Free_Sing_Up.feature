@ux _cx @feature
Feature: [Feature]: Free Sign Up
  
  Автоматически сгенерированная feature для FRONT.Auth.Free_Sing_Up
  
  Functional ID: FRONT.Auth.Free_Sing_Up
  Module: FRONT
  Epic: Auth
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Auth" инициализирован


  Scenario: Базовая функциональность [Feature]: Free Sign Up
    Given пользователь авторизован
    When пользователь использует "[Feature]: Free Sign Up"
    Then функционал работает корректно
    And нет ошибок
