package workbench.container.l02.demo;

import workbench.container.l02.Container;
import workbench.container.l02.demo.app.CardIssuerClient;
import workbench.container.l02.demo.app.FlakyIssuer;
import workbench.container.l02.demo.app.IssuerScript;
import workbench.container.l02.demo.app.IssuerUnavailableException;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.List;

/** authorizeAndCapture, with one capture timing out: what does the issuer see? */
public class RetryDemo {
    public static void main(String[] args) {
        Container c = new Container(List.of(IssuerScript.class, FlakyIssuer.class));
        IssuerScript script = c.get(IssuerScript.class);
        script.captureFailures.set(1);
        String result = c.get(CardIssuerClient.class).authorizeAndCapture("4111111111111111", 12_000);
        System.out.println("container's proxy:  " + result + ", issuer saw " + script.seen);
        System.out.println("  timed calls: " + c.callLog().names());

        IssuerScript naiveScript = new IssuerScript();
        naiveScript.captureFailures.set(1);
        FlakyIssuer target = new FlakyIssuer(naiveScript);
        InvocationHandler retryEverything = (proxy, method, a) -> {        // retries any method, default ones too
            for (int attempt = 1; ; attempt++) {
                try {
                    return method.invoke(target, a);                       // the default body runs on the target
                } catch (InvocationTargetException e) {
                    if (attempt == 3 || !(e.getCause() instanceof IssuerUnavailableException)) throw e.getCause();
                }
            }
        };
        CardIssuerClient naive = (CardIssuerClient) Proxy.newProxyInstance(
                CardIssuerClient.class.getClassLoader(), new Class<?>[] {CardIssuerClient.class}, retryEverything);
        System.out.println("retry the shell:    " + naive.authorizeAndCapture("4111111111111111", 12_000)
                + ", issuer saw " + naiveScript.seen);
    }
}
