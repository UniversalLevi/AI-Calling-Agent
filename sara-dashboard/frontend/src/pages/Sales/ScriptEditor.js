import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';

const ScriptEditor = () => {
  const [scripts, setScripts] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
  const [formData, setFormData] = useState({
    productId: '',
    scriptType: 'greeting',
    technique: 'Consultative',
    stage: 'Presentation',
    content: '',
    language: 'en',
    priority: 1,
    conditions: {
      triggers: [],
      minQualificationScore: 0,
      maxCallDuration: 300
    },
    variables: [],
    isActive: true
  });

  useEffect(() => {
    fetchScripts();
    fetchProducts();
  }, []);

  const fetchScripts = async () => {
    try {
      const response = await fetch('/api/sales/scripts');
      const data = await response.json();
      if (data.success) {
        setScripts(data.data);
      }
    } catch (error) {
      console.error('Error fetching scripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/sales/products');
      const data = await response.json();
      if (data.success) {
        setProducts(data.data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingScript 
        ? `/api/sales/scripts/${editingScript._id}`
        : '/api/sales/scripts';
      const method = editingScript ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      if (result.success) {
        fetchScripts();
        setShowModal(false);
        setEditingScript(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error saving script:', error);
    }
  };

  const handleDelete = async (scriptId) => {
    if (window.confirm('Are you sure you want to delete this script?')) {
      try {
        const response = await fetch(`/api/sales/scripts/${scriptId}`, {
          method: 'DELETE'
        });
        const result = await response.json();
        if (result.success) {
          fetchScripts();
        }
      } catch (error) {
        console.error('Error deleting script:', error);
      }
    }
  };

  const handleEdit = (script) => {
    setEditingScript(script);
    setFormData(script);
    setShowModal(true);
  };

  const resetForm = () => {
    setFormData({
      productId: '',
      scriptType: 'greeting',
      technique: 'Consultative',
      stage: 'Presentation',
      content: '',
      language: 'en',
      priority: 1,
      conditions: {
        triggers: [],
        minQualificationScore: 0,
        maxCallDuration: 300
      },
      variables: [],
      isActive: true
    });
  };

  const getScriptTypeColor = (type) => {
    const colors = {
      greeting: 'bg-green-100 text-green-800',
      qualification: 'bg-blue-100 text-blue-800',
      presentation: 'bg-purple-100 text-purple-800',
      objection: 'bg-red-100 text-red-800',
      closing: 'bg-yellow-100 text-yellow-800',
      upsell: 'bg-indigo-100 text-indigo-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getTechniqueColor = (technique) => {
    const colors = {
      SPIN: 'bg-blue-100 text-blue-800',
      Consultative: 'bg-green-100 text-green-800',
      Challenger: 'bg-red-100 text-red-800',
      Generic: 'bg-gray-100 text-gray-800'
    };
    return colors[technique] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Script Editor</h1>
        <button
          onClick={() => {
            resetForm();
            setEditingScript(null);
            setShowModal(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Script
        </button>
      </div>

      {/* Scripts List */}
      <div className="space-y-4">
        {scripts.map((script) => {
          const product = products.find(p => p._id === script.productId);
          return (
            <div key={script._id} className="bg-white rounded-lg shadow-md p-6 border">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScriptTypeColor(script.scriptType)}`}>
                      {script.scriptType}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTechniqueColor(script.technique)}`}>
                      {script.technique}
                    </span>
                    <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
                      {script.language}
                    </span>
                    <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                      Priority: {script.priority}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {product ? product.name : 'Unknown Product'}
                  </h3>
                  
                  <p className="text-gray-600 mb-4">{script.content}</p>
                  
                  <div className="text-sm text-gray-500">
                    <p>Stage: {script.stage}</p>
                    <p>Success Rate: {script.successRate}%</p>
                    <p>Usage Count: {script.usageCount}</p>
                  </div>
                </div>
                
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleEdit(script)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(script._id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">
              {editingScript ? 'Edit Script' : 'Add New Script'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Product
                  </label>
                  <select
                    value={formData.productId}
                    onChange={(e) => setFormData({ ...formData, productId: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select Product</option>
                    {products.map(product => (
                      <option key={product._id} value={product._id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Script Type
                  </label>
                  <select
                    value={formData.scriptType}
                    onChange={(e) => setFormData({ ...formData, scriptType: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="greeting">Greeting</option>
                    <option value="qualification">Qualification</option>
                    <option value="presentation">Presentation</option>
                    <option value="objection">Objection</option>
                    <option value="closing">Closing</option>
                    <option value="upsell">Upsell</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Technique
                  </label>
                  <select
                    value={formData.technique}
                    onChange={(e) => setFormData({ ...formData, technique: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="SPIN">SPIN</option>
                    <option value="Consultative">Consultative</option>
                    <option value="Challenger">Challenger</option>
                    <option value="Generic">Generic</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stage
                  </label>
                  <select
                    value={formData.stage}
                    onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Situation">Situation</option>
                    <option value="Problem">Problem</option>
                    <option value="Implication">Implication</option>
                    <option value="Need-payoff">Need-payoff</option>
                    <option value="Presentation">Presentation</option>
                    <option value="Closing">Closing</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                  </label>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
              </div>

              {/* Script Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Script Content
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={6}
                  placeholder="Enter your script content here. Use {product_name}, {product_price} for dynamic content..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Use variables like {`{product_name}`}, {`{product_price}`} for dynamic content
                </p>
              </div>

              {/* Conditions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Conditions
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">
                      Min Qualification Score
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="40"
                      value={formData.conditions.minQualificationScore}
                      onChange={(e) => setFormData({
                        ...formData,
                        conditions: {
                          ...formData.conditions,
                          minQualificationScore: parseInt(e.target.value)
                        }
                      })}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">
                      Max Call Duration (seconds)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="600"
                      value={formData.conditions.maxCallDuration}
                      onChange={(e) => setFormData({
                        ...formData,
                        conditions: {
                          ...formData.conditions,
                          maxCallDuration: parseInt(e.target.value)
                        }
                      })}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Status */}
              <div className="flex items-center gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="mr-2"
                  />
                  Active Script
                </label>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingScript ? 'Update Script' : 'Create Script'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScriptEditor;
