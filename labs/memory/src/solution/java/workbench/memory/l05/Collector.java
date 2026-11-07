package workbench.memory.l05;

/** The HotSpot collectors this lesson compares. ZGC means generational ZGC, the only kind from JDK 24 on. */
public enum Collector {
    SERIAL, PARALLEL, G1, ZGC, SHENANDOAH, SHENANDOAH_GENERATIONAL, EPSILON
}
