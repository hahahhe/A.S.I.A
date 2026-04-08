# Refactoring Plan #

## 1. Background
본 프로젝트는 초기 기능 구현에 중점을 두고 개발되었으며, 그 결과 app.py에 모든 로직이 포함된 구조로 완성되었습니다.
현재 기능은 정상 동작하지만, 코드의 유지보수성과 확장성 측면에서 개선이 필요하다 판단하였습니다.

## 2. Problem Statement
현재 코드베이스는 다음과 같은 문제를 가지고 있습니다:
- 단일 파일 구조
- 강한 결합
- 전역 상태 사용
- 가독성 저하
- 확장성 부족

## 3. Objectives
본 리펙토링의 주요 목표는 다음과 같습니다:
- 코드의 가독성과 유지보수성 향상
- 향후 기능 확장을 고려한 구조 개선

## 4. Strategy
### 4.1 Layered Architecture
프로젝트를 다음과 같은 구조로 재구성합니다:
- Routes Layer: Http 요청/응답 처리
- Service Layer: 비즈니스 로직 수행
- Model Layer: AI 모델 관련 작업 
- Utils Layer: 공통 유틸 함수

### 4.2 Key Changes
- 로직들의 종류별 분리
- 전역 변수 제거
- 함수가 하나의 역할만 수행하도록 분리

## 5. Branch
- main: 최종
- develop: 통합 브랜치
- modulize: 리팩토링 작업

