package workbench.container.l01.app;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Where static initializers report. The flag lives here, not in ScanProbe, because reading a
 * static field of ScanProbe would itself initialize ScanProbe.
 */
public final class InitLog {
    public static final Set<String> INITIALIZED = ConcurrentHashMap.newKeySet();

    private InitLog() {}
}
