# senior_research
# Measuring Defender Cost and Attacker Cost of Argon2id, PBKDF2, and bcrypt Password Hashing on a Consumer CPU

## Overview

Passwords are commonly used to protect online accounts, but database breaches can expose stored password hashes to attackers. Password hashing algorithms help protect users by making it more difficult and time-consuming to guess passwords. However, stronger hashing settings also require more processing time and memory from the systems using them.

This project investigates the trade-offs between password security and system performance by comparing three password-hashing algorithms: Argon2id, PBKDF2, and bcrypt.

## Project Objective

The objective of this research is to measure how different Argon2id settings, including memory usage, iteration count, and parallelism, affect the cost of password hashing for legitimate systems and the cost of password guessing for attackers.

The project will compare these measurements against PBKDF2 and bcrypt to evaluate their relative performance and resistance to CPU-based password attacks. It will also use a budget model to estimate the financial cost of attempting different numbers of password guesses.

## Approach

The experiments will be conducted using Python on a personal computer. Hashcat and John the Ripper will be used to measure password-guessing performance, while Python libraries will measure hashing time and memory consumption.

The results will be analyzed using tables and graphs to illustrate the relationship between defender resource requirements and attacker costs.

## Expected Outcome

The goal is to identify password-hashing configurations that provide a reasonable balance between security and performance. The research will also examine whether increasing Argon2id's memory requirements continues to provide meaningful benefits against attackers or eventually produces diminishing returns.


