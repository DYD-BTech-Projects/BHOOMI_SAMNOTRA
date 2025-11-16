# srtf_logic.py
# Backend SRTF scheduling logic (separate file)
# Returns processes (with CT/TAT/WT), average WT/TAT, and the gantt list (per time unit)

def srtf_scheduling(processes):
    """
    Input:
      processes: list of dicts with keys:
        - 'pid' (string, e.g. "P1")
        - 'arrival' (int)
        - 'burst' (int)

    Returns:
      (procs, avg_wt, avg_tat, gantt)
        procs: list of dicts augmented with 'ct','tat','wt'
        avg_wt, avg_tat: floats
        gantt: list of pid strings per time unit, e.g. ['Idle','P1','P1','P2',...]
    """
    procs = [dict(p) for p in processes]
    if not procs:
        return [], 0.0, 0.0, []

    for p in procs:
        if 'arrival_time' in p and 'arrival' not in p:
            p['arrival'] = p['arrival_time']
        if 'burst_time' in p and 'burst' not in p:
            p['burst'] = p['burst_time']

    procs.sort(key=lambda x: x['arrival'])

    n = len(procs)
    remaining = [p['burst'] for p in procs]
    completed = 0
    t = 0
    gantt = []

    while completed < n:
        idx = -1
        min_rem = 10**9
        for i in range(n):
            if procs[i]['arrival'] <= t and remaining[i] > 0:
                if remaining[i] < min_rem:
                    min_rem = remaining[i]
                    idx = i

        if idx == -1:
            gantt.append("Idle")
            t += 1
            continue

        gantt.append(procs[idx]['pid'])
        remaining[idx] -= 1
        t += 1

        if remaining[idx] == 0:
            completed += 1
            finish = t
            procs[idx]['ct'] = finish
            procs[idx]['tat'] = finish - procs[idx]['arrival']
            procs[idx]['wt'] = procs[idx]['tat'] - procs[idx]['burst']
            if procs[idx]['wt'] < 0:
                procs[idx]['wt'] = 0

    total_wt = sum(p.get('wt', 0) for p in procs)
    total_tat = sum(p.get('tat', 0) for p in procs)
    avg_wt = total_wt / n
    avg_tat = total_tat / n

    return procs, avg_wt, avg_tat, gantt
