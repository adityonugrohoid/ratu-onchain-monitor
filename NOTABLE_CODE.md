# Notable Code: RATU On-chain Monitor

This document highlights key code sections that demonstrate the technical strengths and architectural patterns implemented in this on-chain analytics tool.

## Overview

RATU On-chain Monitor is an on-chain token holder analytics and whale tracking tool using the Ankr API. The system demonstrates prototyping-focused on-chain analytics patterns including three-mode architecture, pagination handling, and known label identification.

---

## 1. Three-Mode Architecture

**File:** Main implementation  
**Lines:** Mode selection logic

The system provides three modes: (1) Basic Info for fast token metadata (~5 seconds), (2) Top Holders with known labels (~3 seconds), (3) Full Snapshot with pagination (2-5 minutes).

**Why it's notable:**
- Balances speed vs completeness
- Users choose based on needs
- Fast basic info for quick analysis
- Full snapshot for complete holder lists

---

## 2. Pagination Handling for Large Datasets

**File:** Snapshot implementation  
**Lines:** Pagination loop logic

The system implements pagination using Ankr getTokenHolders API with page parameter, continuing until all holders are retrieved.

**Why it's notable:**
- Handles tokens with millions of holders
- Continues until all holders retrieved
- Handles large holder counts (197K+ holders) in 2-5 minutes
- Enables complete holder analysis for any token size

---

## 3. Known Label Identification

**File:** Label database implementation  
**Lines:** Label matching logic

The system maintains a database of known wallet addresses and automatically identifies exchanges (Binance, OKX, Bybit) and special addresses (Burn, Null).

**Why it's notable:**
- Automatically labels holders in output
- Provides context for holder analysis
- Identifies exchanges and special addresses
- Enables whale tracking with context

---

## 4. Snapshot Comparison

**File:** Snapshot saving logic  
**Lines:** Timestamped JSON generation

The system saves snapshots as timestamped JSON files enabling comparison of holder distributions over time.

**Why it's notable:**
- Timestamped JSON snapshots
- Enables programmatic comparison
- Tracks holder changes over time
- Supports whale tracking analysis

---

## Architecture Highlights

### Three-Mode Design

1. **Basic Info Mode**: Fast token metadata and top holders
2. **Top Holders Mode**: Known label identification
3. **Full Snapshot Mode**: Complete holder lists with pagination

### Design Patterns Used

1. **Multi-Mode Pattern**: Different modes for different needs
2. **Pagination Pattern**: Handles large datasets efficiently
3. **Label Database Pattern**: Known address identification
4. **Snapshot Pattern**: Time-series comparison capability

---

## Technical Strengths Demonstrated

- **Flexible Architecture**: Three modes for different use cases
- **Scalable Pagination**: Handles millions of holders
- **Context-Aware Analysis**: Known label identification
- **Time-Series Tracking**: Snapshot comparison for changes
- **Multi-Chain Support**: 6 major blockchain networks
