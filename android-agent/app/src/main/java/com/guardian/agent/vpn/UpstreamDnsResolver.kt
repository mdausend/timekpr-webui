package com.guardian.agent.vpn

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties
import android.net.Network
import android.net.VpnService
import android.util.Log
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.UnknownHostException

internal class UpstreamDnsResolver(
    context: Context,
    private val vpnService: VpnService,
    upstreamNetwork: Network?,
) {
    private val connectivityManager: ConnectivityManager? by lazy {
        try {
            context.getSystemService(ConnectivityManager::class.java)
        } catch (_: Exception) {
            null
        }
    }

    val network: Network? = upstreamNetwork ?: try {
        VpnNetworkCapture.findUnderlyingNetwork(context)
    } catch (_: Exception) {
        null
    }
    val servers: List<InetAddress> = resolveUpstreamServers(network)

    fun resolve(parsed: DnsPacketHandler.ParsedDnsQuery): ByteArray? {
        return resolveRaw(parsed.dnsPayload, parsed.queryName)
    }

    fun resolveRaw(dnsPayload: ByteArray, queryName: String): ByteArray? {
        return forward(dnsPayload)
    }

    fun forward(query: ByteArray): ByteArray? {
        for (server in servers) {
            try {
                DatagramSocket().use { socket ->
                    bindSocket(socket)
                    socket.soTimeout = TIMEOUT_MS
                    socket.send(DatagramPacket(query, query.size, server, 53))
                    val buffer = ByteArray(4096)
                    val response = DatagramPacket(buffer, buffer.size)
                    socket.receive(response)
                    return buffer.copyOf(response.length)
                }
            } catch (e: Exception) {
                Log.d(TAG, "Raw upstream DNS query failed via ${server.hostAddress}", e)
            }
        }
        return null
    }

    private fun bindSocket(socket: DatagramSocket) {
        if (!vpnService.protect(socket)) {
            Log.w(TAG, "Failed to protect upstream DNS socket")
        }
        val upstream = network
        if (upstream != null) {
            try {
                upstream.bindSocket(socket)
            } catch (e: Exception) {
                Log.d(TAG, "Failed to bind socket to upstream network: ${e.message}")
            }
        }
    }

    private fun resolveUpstreamServers(network: Network?): List<InetAddress> {
        val servers = linkedSetOf<InetAddress>()
        val linkProperties: LinkProperties? = network?.let { connectivityManager?.getLinkProperties(it) }
        linkProperties?.dnsServers
            ?.filterIsInstance<Inet4Address>()
            ?.forEach { servers.add(it) }
        FALLBACK_SERVERS.forEach { servers.add(it) }
        return servers.toList()
    }

    companion object {
        private const val TAG = "UpstreamDnsResolver"
        private const val TIMEOUT_MS = 3_000
        private val FALLBACK_SERVERS = listOf(
            InetAddress.getByName("8.8.8.8"),
            InetAddress.getByName("1.1.1.1"),
        )
    }
}
