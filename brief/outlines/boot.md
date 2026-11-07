# Track: boot, "Startup and footprint" (lab: labs/startup, package workbench.startup.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/startup_footprint.md". Much of this track is commands, not code: put commands
in Try-it steps with real measured output from the notes (state the machine). Leyden flags need JDK
24/25 and native image needs GraalVM: say so plainly. Gradle labs (release 21) must still be real
code with tests: lazy holders, class-load counting, metadata files validated by tests, a CRaC-style
Resource lifecycle simulated with a small interface. Link to cls-01 (class loading) and pat-01 (lazy init).

Lessons:
- boot-01 Why the JVM starts slowly, and how to measure it: class loading, static init, JIT warm-up,
  framework scanning, RSS vs heap; -Xlog:class+load, time-to-first-request. Lab: move expensive static
  init behind a holder and prove (with a test) it runs only when needed.
- boot-02 Class data sharing and Project Leyden's AOT cache: default CDS, AppCDS, dynamic archives,
  JEP 483/514/515 commands for a training run and a production run.
- boot-03 GraalVM native image and Quarkus native: closed world, build-time init, reachability
  metadata for reflection and proxies (exact JSON from the notes), @RegisterForReflection, trade-offs.
  Lab: write metadata for a reflective proxy and a reflective class; a test validates it.
- boot-04 CRaC, and choosing a startup strategy: checkpoint/restore, org.crac Resource, which JDKs
  ship it, Lambda SnapStart, and a decision table for AppCDS/Leyden vs native vs CRaC vs nothing.
