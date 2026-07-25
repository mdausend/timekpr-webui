package com.guardian.agent.vpn

import android.content.Context
import android.net.VpnService
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.net.DatagramSocket
import java.net.InetAddress

class UpstreamDnsResolverTest {

    private class TestVpnService : VpnService() {
        var protectedSocketCount = 0

        override fun protect(socket: DatagramSocket?): Boolean {
            if (socket != null) {
                protectedSocketCount++
            }
            return true
        }
    }

    @Test
    fun verifiesFallbackDnsServers() {
        val testVpn = TestVpnService()
        val resolver = UpstreamDnsResolver(testVpn, testVpn, null)
        assertNotNull(resolver.servers)
        assertTrue(resolver.servers.isNotEmpty())
        assertTrue(resolver.servers.contains(InetAddress.getByName("8.8.8.8")))
        assertTrue(resolver.servers.contains(InetAddress.getByName("1.1.1.1")))
    }
}
