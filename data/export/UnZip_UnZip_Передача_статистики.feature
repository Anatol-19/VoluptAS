@api @feature
Feature: [Feature]: Пердача UnZip
  
  Автоматически сгенерированная feature для UnZip.UnZip.Передача_статистики
  
  Functional ID: UnZip.UnZip.Передача_статистики
  Module: UnZip
  Epic: UnZip
  Responsible QA: Анатолий
  Responsible Dev: N/A

  Background:
    Given модуль "UnZip" доступен
    And эпик "UnZip" инициализирован


  Scenario: Базовая функциональность [Feature]: Пердача UnZip
    Given пользователь авторизован
    When пользователь использует "[Feature]: Пердача UnZip"
    Then функционал работает корректно
    And нет ошибок
