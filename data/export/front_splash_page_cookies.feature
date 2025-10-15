@perfom @feature
Feature: [Feature]: Age cookies
  
  Отображение контента и корректных ответов при наличии куки Age = true
  
  Functional ID: front.splash_page.cookies
  Module: FRONT
  Epic: Slash Page
  Responsible QA: Никита
  Responsible Dev: N/A

  Background:
    Given модуль "FRONT" доступен
    And эпик "Slash Page" инициализирован


  Scenario: Базовая функциональность [Feature]: Age cookies
    Given пользователь авторизован
    When пользователь использует "[Feature]: Age cookies"
    Then функционал работает корректно
    And нет ошибок
