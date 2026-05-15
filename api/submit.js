const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY
);

module.exports = async (req, res) => {
    // 只接受 POST
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    // CORS（允许你的 HTML 页面跨域请求）
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    try {
        const payload = req.body;

        // 基础校验
        if (!payload.user_id || !payload.test_results || payload.test_results.length === 0) {
            return res.status(400).json({ error: '无效的提交数据' });
        }

        const { error } = await supabase.from('survey_results').insert([{
            user_id: payload.user_id,
            device_type: payload.test_environment?.device_type || null,
            survey_timestamp: payload.test_environment?.timestamp || null,
            age: payload.demographics?.age || null,
            gender: payload.demographics?.gender || null,
            listening_frequency: payload.demographics?.listening_frequency || null,
            training_years: payload.demographics?.training_years || null,
            instrument: payload.demographics?.instrument || null,
            test_results: payload.test_results,
            difference_perception: payload.qualitative_feedback?.difference_perception || null,
            issues: payload.qualitative_feedback?.issues || null
        }]);

        if (error) throw error;

        return res.status(200).json({ success: true });
    } catch (err) {
        console.error('Submit error:', err);
        return res.status(500).json({ 
            error: '服务器内部错误',
            detail: err.message || String(err),
            hasUrl: !!process.env.SUPABASE_URL,
            hasKey: !!process.env.SUPABASE_ANON_KEY
        });
    }
};
