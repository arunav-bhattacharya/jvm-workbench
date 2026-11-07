package workbench.container.l01.app;

import workbench.container.l01.Component;

/** No test ever creates this one. Its static initializer writes to InitLog if anything runs it. */
@Component
public class ScanProbe {
    static {
        InitLog.INITIALIZED.add("ScanProbe");
    }
}
