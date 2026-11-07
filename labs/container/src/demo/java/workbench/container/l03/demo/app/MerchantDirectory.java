package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class MerchantDirectory {
    public String categoryOf(String merchantId) { return merchantId.startsWith("m_7") ? "5814" : "5411"; }
}
