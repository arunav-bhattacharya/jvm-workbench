# Track: dop, "Modern Java data modeling" (lab: labs/modernjava, package workbench.modernjava.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/modern_java_data_modeling.md" (real javac errors captured on JDK 21). Labs compile
with release 21: records, sealed types, switch and record patterns are all final there. Features from
JDK 22+ (unnamed variables JEP 456, primitive patterns, withers) go in single-file demos under
labs/modernjava/preview/ that say which JDK they need. Every lesson compares with Kotlin (data class,
sealed, when, guards). Link to pat-09 (State with sealed types) and pat-10 (Visitor vs patterns).

Lessons:
- dop-01 Records: canonical and compact constructors, validation, accessors, equals/hashCode,
  shallow immutability and defensive copies, records vs Kotlin data classes. Lab: payment value records.
- dop-02 Sealed types: permits, final/sealed/non-sealed, module and package rules, exhaustiveness.
- dop-03 Pattern matching with switch and record patterns: guards, null handling, dominance,
  exhaustive switches and the exact compiler errors. Lab: a fee calculator over a sealed hierarchy.
- dop-04 Data-oriented programming, and Project Valhalla: model the data, make illegal states
  unrepresentable, operations apart from data, the expression problem; Valhalla's status stated carefully.
