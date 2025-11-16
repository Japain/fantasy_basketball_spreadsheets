# Conditional Formatting for Remaining Salary

## Feature Summary

Added conditional formatting to the "Remaining Salary" column/row in Google Sheets to visually highlight budget status:

- **GREEN** 🟢: Remaining Salary > $0 (team has budget remaining)
- **RED** 🔴: Remaining Salary ≤ $0 (team at limit or over budget)

## Implementation Details

### Colors Used

**Green (Budget Remaining)**:
- RGB: (0.7, 0.9, 0.7)
- Light green background
- Applied when: Remaining Salary > 0

**Red (At/Over Limit)**:
- RGB: (0.95, 0.7, 0.7)
- Light red/pink background
- Applied when: Remaining Salary ≤ 0

### Where Applied

1. **Summary Sheet**:
   - Column E ("Remaining Salary") for all team rows
   - Rows 21+ (team data rows)

2. **Individual Team Sheets**:
   - Row "REMAINING SALARY" in the summary section
   - Column D (value column)

## Test Results

Test spreadsheet created: https://docs.google.com/spreadsheets/d/1vhhPGj01AMr3r38UslUvWm0zETDKUtOJ0wjxqquf1vU/edit

**Test Scenarios**:

1. **Team With Budget**
   - Total Salary: $150
   - Remaining: $75
   - Expected: GREEN ✓

2. **Team At Limit**
   - Total Salary: $225
   - Remaining: $0
   - Expected: RED ✗

3. **Team Over Budget**
   - Total Salary: $240
   - Remaining: -$15
   - Expected: RED ✗

## Code Changes

### Files Modified:

1. **src/sheet_generator.py**:
   - Added conditional format rules to `create_summary_sheet()`
   - Added conditional format rules to `create_team_sheet()`
   - Uses Google Sheets API `addConditionalFormatRule` requests

### Technical Implementation:

```python
# Green formatting (> 0)
{
    'addConditionalFormatRule': {
        'rule': {
            'ranges': [...],
            'booleanRule': {
                'condition': {
                    'type': 'NUMBER_GREATER',
                    'values': [{'userEnteredValue': '0'}]
                },
                'format': {
                    'backgroundColor': {
                        'red': 0.7,
                        'green': 0.9,
                        'blue': 0.7
                    }
                }
            }
        }
    }
}

# Red formatting (≤ 0)
{
    'addConditionalFormatRule': {
        'rule': {
            'ranges': [...],
            'booleanRule': {
                'condition': {
                    'type': 'NUMBER_LESS_THAN_EQ',
                    'values': [{'userEnteredValue': '0'}]
                },
                'format': {
                    'backgroundColor': {
                        'red': 0.95,
                        'green': 0.7,
                        'blue': 0.7
                    }
                }
            }
        }
    }
}
```

## Usage

No changes required to usage! The conditional formatting is automatically applied when generating any league report:

```bash
# Standard usage
uv run python main.py

# With custom options
uv run python main.py --title "Week 5 Report" --verbose
```

The generated spreadsheet will automatically include the color-coded "Remaining Salary" highlighting.

## Benefits

- **Quick Visual Identification**: Instantly see which teams are over/at budget
- **Budget Management**: Helps managers track their remaining salary cap
- **League Monitoring**: Commissioners can quickly identify budget violations
- **Professional Presentation**: Clean, color-coded data visualization
