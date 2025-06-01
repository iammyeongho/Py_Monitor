#!/bin/bash

# 현재 날짜 가져오기 (YYYYMMDD 형식)
CURRENT_DATE=$(date +"%Y%m%d")

# Git 사용자 이름 가져오기
GIT_USERNAME=$(git config user.name)

# 변경된 파일 목록 가져오기
CHANGED_FILES=$(git status --porcelain | awk '{print $2}')

# 작업 유형 판단 함수
determine_work_type() {
    local files=$1
    local has_docs=false
    local has_tests=false
    local has_features=false
    local has_fixes=false

    for file in $files; do
        # 파일 확장자 확인
        extension="${file##*.}"
        
        # docs 디렉토리 확인
        if [[ $file == docs/* ]]; then
            has_docs=true
        fi
        
        # tests 디렉토리 확인
        if [[ $file == tests/* ]]; then
            has_tests=true
        fi
        
        # 기능 추가 확인 (새로운 파일 생성)
        if [[ $file == app/* ]] && [[ ! -f $file ]]; then
            has_features=true
        fi
        
        # 버그 수정 확인 (기존 파일 수정)
        if [[ $file == app/* ]] && [[ -f $file ]]; then
            has_fixes=true
        fi
    done

    # 우선순위에 따라 작업 유형 반환
    if [ "$has_docs" = true ]; then
        echo "docs"
    elif [ "$has_tests" = true ]; then
        echo "test"
    elif [ "$has_features" = true ]; then
        echo "feature"
    elif [ "$has_fixes" = true ]; then
        echo "fix"
    else
        echo "feature"  # 기본값
    fi
}

# 작업 유형 결정
WORK_TYPE=$(determine_work_type "$CHANGED_FILES")

# 브랜치 이름 생성
BRANCH_NAME="${WORK_TYPE}/${CURRENT_DATE}_${GIT_USERNAME}_back_${WORK_TYPE}"

# 새 브랜치 생성
git checkout -b "$BRANCH_NAME"

echo "Created new branch: $BRANCH_NAME"
echo "Work type: $WORK_TYPE"
echo "Date: $CURRENT_DATE"
echo "Username: $GIT_USERNAME" 